import numpy as np

"""
Gonna use this to write math functions, either for learning purposes or something thats nich and helpful 
"""

class PCA():
    """
    Assumes that the data fed into this class is an array of asset returns in a numpy array
    May need to change that at some point depending on my datasource
    most of this code was written by following someone elses implementation -> https://bagheri365.github.io/blog/Principal-Component-Analysis-from-Scratch/
    """
    
    def __init__(self, data, n_components):
        self.data = data
        self.n_components = n_components
        self.components = None
        self.explained_variance_ratio = None
        self.cum_explained_variance = None

    def _standardize_data(self):
        return (self.data - np.mean(self.data, axis=0)) / np.std(self.data, axis=0)
    
    def _covariance_matrix(self, data):
        return np.cov(data, rowvar=False)
        
    def _sort_eigens(self, eig_vals, eig_vecs):
        idx = eig_vals.argsort()[::-1]
        return eig_vals[idx], eig_vecs[:, idx]

    def fit(self):
        """
        Performs PCA on the data.
        """
        normalized_data = self._standardize_data()
        cov_matrix = self._covariance_matrix(normalized_data)
        eigen_values, eigen_vectors = np.linalg.eig(cov_matrix)
        eig_vals_sorted, eig_vecs_sorted = self._sort_eigens(eigen_values, eigen_vectors)

        self.components = eig_vecs_sorted[:, :self.n_components].T
        self.explained_variance_ratio = eig_vals_sorted[:self.n_components] / np.sum(eig_vals_sorted)
        self.cum_explained_variance = np.cumsum(self.explained_variance_ratio)

    def transform(self, X):
        """
        Applies the dimensionality reduction on X
        """
        if self.components is None:
            raise ValueError("PCA has not been fitted. Call fit() before transform()")
        return np.dot(X - np.mean(self.data, axis=0), self.components.T) 
