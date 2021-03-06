#!/usr/bin/env python3
import torch
import torch.nn as nn
import torch.jit as jit
import warnings
from torch import Tensor
from torch.nn import Parameter
from collections import namedtuple
from typing import List, Tuple, Optional


class SubLSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(SubLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.weight_ih = Parameter(torch.randn(4 * hidden_size, input_size))
        self.weight_hh = Parameter(torch.randn(4 * hidden_size, hidden_size))
        self.bias_ih = Parameter(torch.randn(4 * hidden_size))
        self.bias_hh = Parameter(torch.randn(4 * hidden_size))

    def forward(self,
                input: Tensor,
                state: Tuple[Tensor, Tensor]
                ) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:

        hx, cx = state
        gates = (torch.mm(input, self.weight_ih.t()) + self.bias_ih +
                 torch.mm(hx, self.weight_hh.t()) + self.bias_hh).sigmoid()
        ingate, forgetgate, cellgate, outgate = gates.chunk(4, 1)

        cy = (forgetgate * cx) + (cellgate - ingate)
        hy = torch.tanh(cy) - outgate

        return hy, (hy, cy)


class LayerNormSubLSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(LayerNormSubLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.weight_ih = Parameter(torch.randn(4 * hidden_size, input_size))
        self.weight_hh = Parameter(torch.randn(4 * hidden_size, hidden_size))
        # The layernorms provide learnable biases

        self.layernorm_i = nn.LayerNorm(4 * hidden_size)
        self.layernorm_h = nn.LayerNorm(4 * hidden_size)
        self.layernorm_c = nn.LayerNorm(hidden_size)

    def forward(self,
                input: Tensor,
                state: Tuple[Tensor, Tensor]
                ) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:

        hx, cx = state
        igates = self.layernorm_i(torch.mm(input, self.weight_ih.t()))
        hgates = self.layernorm_h(torch.mm(hx, self.weight_hh.t()))
        gates = (igates + hgates).sigmoid()
        ingate, forgetgate, cellgate, outgate = gates.chunk(4, 1)

        cy = self.layernorm_c((forgetgate * cx) + (cellgate - ingate))
        hy = torch.tanh(cy) - outgate

        return hy (hy, cy)


class fixSubLSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(fixSubLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.weight_ih = Parameter(torch.randn(3 * hidden_size, input_size))
        self.weight_hh = Parameter(torch.randn(3 * hidden_size, hidden_size))
        self.bias_ih = Parameter(torch.randn(3 * hidden_size))
        self.bias_hh = Parameter(torch.randn(3 * hidden_size))
        self.forgetgate = Parameter(torch.randn(hidden_size))

    def forward(self,
                input: Tensor,
                state: Tuple[Tensor, Tensor]
                ) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:

        hx, cx = state
        gates = (torch.mm(input, self.weight_ih.t()) + self.bias_ih +
                 torch.mm(hx, self.weight_hh.t()) + self.bias_hh).sigmoid()
        ingate, cellgate, outgate = gates.chunk(3, 1)

        cy = (self.forgetgate.sigmoid() * cx) + (cellgate - ingate)
        hy = torch.tanh(cy) - outgate

        return hy, (hy, cy)


class LayerNormFixSubLSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(LayerNormFixSubLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.weight_ih = Parameter(torch.randn(3 * hidden_size, input_size))
        self.weight_hh = Parameter(torch.randn(3 * hidden_size, hidden_size))
        self.forgetgate = Parameter(torch.randn(hidden_size))
        # The layernorms provide learnable biases

        self.layernorm_i = nn.LayerNorm(3 * hidden_size)
        self.layernorm_h = nn.LayerNorm(3 * hidden_size)
        self.layernorm_c = nn.LayerNorm(hidden_size)

    def forward(self,
                input: Tensor,
                state: Tuple[Tensor, Tensor]
                ) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:

        hx, cx = state
        igates = self.layernorm_i(torch.mm(input, self.weight_ih.t()))
        hgates = self.layernorm_h(torch.mm(hx, self.weight_hh.t()))
        gates = (igates + hgates).sigmoid()
        ingate, cellgate, outgate = gates.chunk(3, 1)

        cy = self.layernorm_c((self.forgetgate.sigmoid() * cx) + (cellgate - ingate))
        hy = torch.tanh(cy) - outgate

        return hy, (hy, cy)


class PremulSubLSTMCell(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(PremulSubLSTMCell, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.weight_hh = Parameter(torch.randn(4 * hidden_size, hidden_size))
        self.bias_hh = Parameter(torch.randn(4 * hidden_size))
    
    
    def forward(self,
                premul_input: Tensor,
                state: Tuple[Tensor, Tensor]
                ) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:

        hx, cx = state
        gates = (premul_input + torch.mm(hx, self.weight_hh.t()) + self.bias_hh).sigmoid()
        ingate, forgetgate, cellgate, outgate = gates.chunk(4, 1)

        cy = (forgetgate * cx) + (cellgate - ingate)
        hy = torch.tanh(cy) - outgate

        return hy, (hy, cy)