"""Advanced data preprocessing components."""
import numpy as np
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, 
    PowerTransformer, QuantileTransformer
)
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import (
    SelectKBest, SelectFromModel, RFE,
    f_classif, mutual_info_classif
)
from sklearn.decomposition import PCA, FastICA, NMF
import pandas as pd
from typing import Optional, Union, List, Dict, Any
import torch
from torch.utils.data import Dataset, DataLoader

class AdvancedPreprocessor:
    """Advanced data preprocessing with multiple strategies."""
    
    def __init__(self):
        """Initialize preprocessor with available methods."""
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler(),
            'power': PowerTransformer(),
            'quantile': QuantileTransformer()
        }
        
        self.imputers = {
            'mean': SimpleImputer(strategy='mean'),
            'median': SimpleImputer(strategy='median'),
            'most_frequent': SimpleImputer(strategy='most_frequent'),
            'knn': KNNImputer()
        }
        
        self.feature_selectors = {
            'kbest': SelectKBest(),
            'model_based': SelectFromModel(estimator=None),
            'rfe': RFE(estimator=None)
        }
        
        self.dim_reducers = {
            'pca': PCA(),
            'ica': FastICA(),
            'nmf': NMF()
        }
        
    def handle_missing_values(self, data: np.ndarray,
                            strategy: str = 'mean',
                            **kwargs) -> np.ndarray:
        """Handle missing values in the dataset."""
        try:
            imputer = self.imputers[strategy]
            if kwargs:
                imputer.set_params(**kwargs)
            return imputer.fit_transform(data)
        except Exception as e:
            raise ValueError(f"Error in missing value imputation: {str(e)}")
            
    def scale_features(self, data: np.ndarray,
                      method: str = 'standard',
                      **kwargs) -> np.ndarray:
        """Scale features using various methods."""
        try:
            scaler = self.scalers[method]
            if kwargs:
                scaler.set_params(**kwargs)
            return scaler.fit_transform(data)
        except Exception as e:
            raise ValueError(f"Error in feature scaling: {str(e)}")
            
    def select_features(self, data: np.ndarray,
                       labels: np.ndarray,
                       method: str = 'kbest',
                       **kwargs) -> np.ndarray:
        """Select most important features."""
        try:
            selector = self.feature_selectors[method]
            if kwargs:
                selector.set_params(**kwargs)
            return selector.fit_transform(data, labels)
        except Exception as e:
            raise ValueError(f"Error in feature selection: {str(e)}")
            
    def reduce_dimensions(self, data: np.ndarray,
                         method: str = 'pca',
                         n_components: Optional[int] = None,
                         **kwargs) -> np.ndarray:
        """Reduce dimensionality of the dataset."""
        try:
            reducer = self.dim_reducers[method]
            if n_components:
                reducer.set_params(n_components=n_components)
            if kwargs:
                reducer.set_params(**kwargs)
            return reducer.fit_transform(data)
        except Exception as e:
            raise ValueError(f"Error in dimensionality reduction: {str(e)}")

class TimeSeriesPreprocessor:
    """Specialized preprocessor for time series data."""
    
    @staticmethod
    def create_sequences(data: np.ndarray,
                        sequence_length: int,
                        target_size: int = 1) -> tuple:
        """Create sequences for time series prediction."""
        sequences = []
        targets = []
        
        for i in range(len(data) - sequence_length - target_size + 1):
            seq = data[i:(i + sequence_length)]
            target = data[i + sequence_length:i + sequence_length + target_size]
            sequences.append(seq)
            targets.append(target)
            
        return np.array(sequences), np.array(targets)
        
    @staticmethod
    def add_time_features(df: pd.DataFrame,
                         datetime_column: str) -> pd.DataFrame:
        """Add time-based features to the dataset."""
        df = df.copy()
        df[datetime_column] = pd.to_datetime(df[datetime_column])
        
        # Extract time components
        df['hour'] = df[datetime_column].dt.hour
        df['day'] = df[datetime_column].dt.day
        df['month'] = df[datetime_column].dt.month
        df['year'] = df[datetime_column].dt.year
        df['day_of_week'] = df[datetime_column].dt.dayofweek
        df['quarter'] = df[datetime_column].dt.quarter
        
        # Add cyclical features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
        df['month_sin'] = np.sin(2 * np.pi * df['month']/12)
        df['month_cos'] = np.cos(2 * np.pi * df['month']/12)
        
        return df
        
    @staticmethod
    def handle_seasonality(data: np.ndarray,
                          period: int,
                          method: str = 'difference') -> np.ndarray:
        """Handle seasonality in time series data."""
        if method == 'difference':
            return data[period:] - data[:-period]
        elif method == 'ratio':
            return data[period:] / data[:-period]
        else:
            raise ValueError(f"Unknown seasonality handling method: {method}")

class TextPreprocessor:
    """Specialized preprocessor for text data."""
    
    def __init__(self):
        """Initialize text preprocessor."""
        try:
            import nltk
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
            from nltk.tokenize import word_tokenize
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer
            
            self.tokenizer = word_tokenize
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
        except ImportError:
            raise ImportError("NLTK is required for text preprocessing")
            
    def preprocess_text(self, text: str,
                       remove_stopwords: bool = True,
                       lemmatize: bool = True) -> List[str]:
        """Preprocess text data."""
        # Tokenize
        tokens = self.tokenizer(text.lower())
        
        # Remove stopwords
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.stop_words]
            
        # Lemmatize
        if lemmatize:
            tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
            
        return tokens
        
    def create_vocabulary(self, texts: List[str],
                         max_vocab_size: Optional[int] = None) -> Dict[str, int]:
        """Create vocabulary from texts."""
        word_freq = {}
        
        for text in texts:
            tokens = self.preprocess_text(text)
            for token in tokens:
                word_freq[token] = word_freq.get(token, 0) + 1
                
        if max_vocab_size:
            sorted_words = sorted(word_freq.items(),
                                key=lambda x: x[1],
                                reverse=True)[:max_vocab_size]
            word_freq = dict(sorted_words)
            
        return {word: idx for idx, word in enumerate(word_freq.keys())}
        
    def texts_to_sequences(self, texts: List[str],
                          vocabulary: Dict[str, int],
                          max_length: Optional[int] = None) -> np.ndarray:
        """Convert texts to sequences of indices."""
        sequences = []
        
        for text in texts:
            tokens = self.preprocess_text(text)
            sequence = [vocabulary.get(token, len(vocabulary))
                       for token in tokens]
                       
            if max_length:
                if len(sequence) < max_length:
                    sequence += [0] * (max_length - len(sequence))
                else:
                    sequence = sequence[:max_length]
                    
            sequences.append(sequence)
            
        return np.array(sequences)

class ImagePreprocessor:
    """Specialized preprocessor for image data."""
    
    @staticmethod
    def normalize_images(images: np.ndarray,
                        method: str = 'minmax') -> np.ndarray:
        """Normalize image pixel values."""
        if method == 'minmax':
            return (images - images.min()) / (images.max() - images.min())
        elif method == 'standard':
            return (images - images.mean()) / images.std()
        else:
            raise ValueError(f"Unknown normalization method: {method}")
            
    @staticmethod
    def resize_images(images: np.ndarray,
                     target_size: tuple) -> np.ndarray:
        """Resize images to target size."""
        try:
            from skimage.transform import resize
            return np.array([resize(img, target_size) for img in images])
        except ImportError:
            raise ImportError("scikit-image is required for image resizing")
            
    @staticmethod
    def extract_image_features(images: np.ndarray,
                             method: str = 'hog') -> np.ndarray:
        """Extract features from images."""
        try:
            from skimage.feature import hog, local_binary_pattern
            
            features = []
            for img in images:
                if method == 'hog':
                    feature = hog(img)
                elif method == 'lbp':
                    feature = local_binary_pattern(
                        img, P=8, R=1, method='uniform'
                    ).flatten()
                else:
                    raise ValueError(f"Unknown feature extraction method: {method}")
                features.append(feature)
                
            return np.array(features)
            
        except ImportError:
            raise ImportError("scikit-image is required for feature extraction")
