"""Advanced model architectures."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Optional, Union, Tuple

class TransformerBlock(nn.Module):
    """Transformer block with multi-head attention."""
    
    def __init__(self, d_model: int, nhead: int,
                 dropout: float = 0.1):
        super().__init__()
        self.attention = nn.MultiheadAttention(d_model, nhead)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model * 4, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
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
                 num_layers: int = 1,
                 dropout: float = 0.1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size,
                           num_layers, dropout=dropout,
                           batch_first=True)
        self.attention = nn.Linear(hidden_size, 1)
        
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        outputs, _ = self.lstm(x)  # [batch, seq_len, hidden]
        attention_weights = F.softmax(self.attention(outputs).squeeze(-1), dim=1)  # [batch, seq_len]
        context = torch.bmm(attention_weights.unsqueeze(1), outputs).squeeze(1)  # [batch, hidden]
        return context, attention_weights

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
    
    def __init__(self, latent_dim: int, img_channels: int):
        super().__init__()
        self.latent_dim = latent_dim
        self.img_channels = img_channels
        
        # Generator
        self.generator = nn.Sequential(
            # Input: latent_dim
            nn.Linear(latent_dim, 512 * 4 * 4),
            nn.ReLU(True),
            nn.Unflatten(1, (512, 4, 4)),  # Reshape to (512, 4, 4)
            
            # State: 512 x 4 x 4
            nn.ConvTranspose2d(512, 256, 4, 2, 1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            # State: 256 x 8 x 8
            nn.ConvTranspose2d(256, 128, 4, 2, 1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            # State: 128 x 16 x 16
            nn.ConvTranspose2d(128, 64, 4, 2, 1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            # State: 64 x 32 x 32
            nn.ConvTranspose2d(64, img_channels, 4, 2, 1, bias=False),
            nn.Tanh()
            # Output: img_channels x 64 x 64
        )
        
        # Discriminator
        self.discriminator = nn.Sequential(
            # Input: img_channels x 64 x 64
            nn.Conv2d(img_channels, 64, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            # State: 64 x 32 x 32
            nn.Conv2d(64, 128, 4, 2, 1, bias=False),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=True),
            # State: 128 x 16 x 16
            nn.Conv2d(128, 256, 4, 2, 1, bias=False),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, inplace=True),
            # State: 256 x 8 x 8
            nn.Conv2d(256, 512, 4, 2, 1, bias=False),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, inplace=True),
            # State: 512 x 4 x 4
            nn.Flatten(),
            nn.Linear(512 * 4 * 4, 1),
            nn.Sigmoid()
        )
    
    def forward(self, z: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through both generator and discriminator."""
        fake_images = self.generator(z.view(-1, self.latent_dim))
        disc_output = self.discriminator(fake_images)
        return fake_images, disc_output
