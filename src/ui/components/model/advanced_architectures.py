"""Advanced model architectures."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Union, Tuple

class TransformerBlock(nn.Module):
    """Transformer block with multi-head attention."""
    
    def __init__(self, embed_dim: int,
                 num_heads: int,
                 ff_dim: int,
                 dropout: float = 0.1):
        super().__init__()
        self.attention = nn.MultiheadAttention(embed_dim, num_heads)
        self.ff = nn.Sequential(
            nn.Linear(embed_dim, ff_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, embed_dim)
        )
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        attended = self.attention(x, x, x)[0]
        x = self.norm1(x + self.dropout(attended))
        feedforward = self.ff(x)
        return self.norm2(x + self.dropout(feedforward))

class ResidualBlock(nn.Module):
    """Residual block for ResNet-style architectures."""
    
    def __init__(self, in_channels: int,
                 out_channels: int,
                 stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels,
                              kernel_size=3, stride=stride,
                              padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels,
                              kernel_size=3, stride=1,
                              padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels,
                         kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )
            
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return F.relu(out)

class LSTMWithAttention(nn.Module):
    """LSTM with attention mechanism."""
    
    def __init__(self, input_size: int,
                 hidden_size: int,
                 num_layers: int,
                 dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size,
                           num_layers, dropout=dropout,
                           batch_first=True)
        self.attention = nn.Linear(hidden_size, 1)
        
    def forward(self, x: torch.Tensor,
                h: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
                ) -> Tuple[torch.Tensor, torch.Tensor]:
        outputs, (h_n, c_n) = self.lstm(x, h)
        attention_weights = F.softmax(self.attention(outputs), dim=1)
        attended = torch.sum(outputs * attention_weights, dim=1)
        return attended, (h_n, c_n)

class DenseNet(nn.Module):
    """DenseNet implementation."""
    
    def __init__(self, growth_rate: int,
                 num_layers: List[int],
                 num_classes: int):
        super().__init__()
        self.features = nn.Sequential()
        in_channels = 64
        
        # Initial convolution
        self.features.add_module('conv0',
            nn.Conv2d(3, in_channels, kernel_size=7,
                     stride=2, padding=3, bias=False))
        self.features.add_module('norm0', nn.BatchNorm2d(in_channels))
        self.features.add_module('relu0', nn.ReLU(inplace=True))
        self.features.add_module('pool0',
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1))
            
        # Dense blocks
        for i, num_layers in enumerate(num_layers):
            block = self._make_dense_block(in_channels,
                                         growth_rate,
                                         num_layers)
            self.features.add_module(f'denseblock{i+1}', block)
            in_channels += num_layers * growth_rate
            
            if i != len(num_layers) - 1:
                trans = self._make_transition(in_channels)
                self.features.add_module(f'transition{i+1}', trans)
                in_channels = in_channels // 2
                
        self.features.add_module('norm5', nn.BatchNorm2d(in_channels))
        self.classifier = nn.Linear(in_channels, num_classes)
        
    def _make_dense_block(self, in_channels: int,
                         growth_rate: int,
                         num_layers: int) -> nn.Sequential:
        layers = []
        for i in range(num_layers):
            layers.append(
                nn.Sequential(
                    nn.BatchNorm2d(in_channels),
                    nn.ReLU(inplace=True),
                    nn.Conv2d(in_channels, growth_rate,
                             kernel_size=3, padding=1, bias=False)
                )
            )
            in_channels += growth_rate
        return nn.Sequential(*layers)
        
    def _make_transition(self, in_channels: int) -> nn.Sequential:
        return nn.Sequential(
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels, in_channels // 2,
                     kernel_size=1, bias=False),
            nn.AvgPool2d(kernel_size=2, stride=2)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.features(x)
        out = F.relu(features)
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = torch.flatten(out, 1)
        return self.classifier(out)

class UNet(nn.Module):
    """U-Net architecture for image segmentation."""
    
    def __init__(self, in_channels: int,
                 out_channels: int,
                 features: List[int] = [64, 128, 256, 512]):
        super().__init__()
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Encoder
        for feature in features:
            self.downs.append(
                nn.Sequential(
                    self._double_conv(in_channels, feature),
                    nn.Dropout(0.1)
                )
            )
            in_channels = feature
            
        # Bottleneck
        self.bottleneck = self._double_conv(features[-1], features[-1]*2)
        
        # Decoder
        for feature in reversed(features):
            self.ups.append(
                nn.ConvTranspose2d(feature*2, feature,
                                 kernel_size=2, stride=2)
            )
            self.ups.append(self._double_conv(feature*2, feature))
            
        self.final_conv = nn.Conv2d(features[0], out_channels,
                                   kernel_size=1)
        
    def _double_conv(self, in_channels: int,
                    out_channels: int) -> nn.Sequential:
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels,
                     kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels,
                     kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip_connections = []
        
        # Encoder
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)
            
        x = self.bottleneck(x)
        skip_connections = skip_connections[::-1]
        
        # Decoder
        for idx in range(0, len(self.ups), 2):
            x = self.ups[idx](x)
            skip_connection = skip_connections[idx//2]
            
            if x.shape != skip_connection.shape:
                x = F.interpolate(x, size=skip_connection.shape[2:])
                
            concat_skip = torch.cat((skip_connection, x), dim=1)
            x = self.ups[idx+1](concat_skip)
            
        return self.final_conv(x)

class GAN(nn.Module):
    """Generative Adversarial Network."""
    
    class Generator(nn.Module):
        def __init__(self, latent_dim: int,
                    output_channels: int):
            super().__init__()
            self.main = nn.Sequential(
                # Layer 1
                nn.ConvTranspose2d(latent_dim, 512,
                                 kernel_size=4, stride=1,
                                 padding=0, bias=False),
                nn.BatchNorm2d(512),
                nn.ReLU(True),
                # Layer 2
                nn.ConvTranspose2d(512, 256,
                                 kernel_size=4, stride=2,
                                 padding=1, bias=False),
                nn.BatchNorm2d(256),
                nn.ReLU(True),
                # Layer 3
                nn.ConvTranspose2d(256, 128,
                                 kernel_size=4, stride=2,
                                 padding=1, bias=False),
                nn.BatchNorm2d(128),
                nn.ReLU(True),
                # Layer 4
                nn.ConvTranspose2d(128, output_channels,
                                 kernel_size=4, stride=2,
                                 padding=1, bias=False),
                nn.Tanh()
            )
            
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.main(x)
            
    class Discriminator(nn.Module):
        def __init__(self, input_channels: int):
            super().__init__()
            self.main = nn.Sequential(
                # Layer 1
                nn.Conv2d(input_channels, 64,
                         kernel_size=4, stride=2,
                         padding=1, bias=False),
                nn.LeakyReLU(0.2, inplace=True),
                # Layer 2
                nn.Conv2d(64, 128,
                         kernel_size=4, stride=2,
                         padding=1, bias=False),
                nn.BatchNorm2d(128),
                nn.LeakyReLU(0.2, inplace=True),
                # Layer 3
                nn.Conv2d(128, 256,
                         kernel_size=4, stride=2,
                         padding=1, bias=False),
                nn.BatchNorm2d(256),
                nn.LeakyReLU(0.2, inplace=True),
                # Layer 4
                nn.Conv2d(256, 1,
                         kernel_size=4, stride=1,
                         padding=0, bias=False),
                nn.Sigmoid()
            )
            
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.main(x)
            
    def __init__(self, latent_dim: int,
                 channels: int):
        super().__init__()
        self.generator = self.Generator(latent_dim, channels)
        self.discriminator = self.Discriminator(channels)
        
    def generate(self, z: torch.Tensor) -> torch.Tensor:
        return self.generator(z)
        
    def discriminate(self, x: torch.Tensor) -> torch.Tensor:
        return self.discriminator(x)
