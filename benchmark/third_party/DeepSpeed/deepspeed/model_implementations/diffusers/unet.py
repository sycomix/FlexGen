'''
Copyright 2022 The Microsoft DeepSpeed Team
'''
import torch


class DSUNet(torch.nn.Module):
    def __init__(self, unet, enable_cuda_graph=True):
        super().__init__()
        self.unet = unet
        # SD pipeline accesses this attribute
        self.in_channels = unet.in_channels
        self.device = self.unet.device
        self.dtype = self.unet.dtype
        self.config = self.unet.config
        self.fwd_count = 0
        self.unet.requires_grad_(requires_grad=False)
        self.unet.to(memory_format=torch.channels_last)
        self.cuda_graph_created = False
        self.enable_cuda_graph = enable_cuda_graph

    def _graph_replay(self, *inputs, **kwargs):
        for i in range(len(inputs)):
            if torch.is_tensor(inputs[i]):
                self.static_inputs[i].copy_(inputs[i])
        for k in kwargs:
            if torch.is_tensor(kwargs[k]):
                self.static_kwargs[k].copy_(kwargs[k])
        self._cuda_graphs.replay()
        return self.static_output

    def forward(self, *inputs, **kwargs):
        if not self.enable_cuda_graph:
            return self._forward(*inputs, **kwargs)
        if not self.cuda_graph_created:
            self._create_cuda_graph(*inputs, **kwargs)
        return self._graph_replay(*inputs, **kwargs)

    def _create_cuda_graph(self, *inputs, **kwargs):
        # warmup to create the workspace and cublas handle
        cuda_stream = torch.cuda.Stream()
        cuda_stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(cuda_stream):
            for _ in range(3):
                ret = self._forward(*inputs, **kwargs)
        torch.cuda.current_stream().wait_stream(cuda_stream)

        # create cuda_graph and assign static_inputs and static_outputs
        self._cuda_graphs = torch.cuda.CUDAGraph()
        self.static_inputs = inputs
        self.static_kwargs = kwargs

        with torch.cuda.graph(self._cuda_graphs):
            self.static_output = self._forward(*self.static_inputs, **self.static_kwargs)

        self.cuda_graph_created = True

    def _forward(self, sample, timestamp, encoder_hidden_states, return_dict=True):
        return self.unet(sample, timestamp, encoder_hidden_states, return_dict)
