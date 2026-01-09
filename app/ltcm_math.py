import numpy as np
from pykalman import KalmanFilter

def run_kalman(x, y):
    """
    卡尔曼滤波计算动态 Beta, Alpha
    """
    delta = 1e-5
    trans_cov = delta / (1 - delta) * np.eye(2)
    obs_mat = np.vstack([x, np.ones(x.shape)]).T[:, np.newaxis]
    
    kf = KalmanFilter(
        n_dim_obs=1, n_dim_state=2,
        initial_state_mean=np.zeros(2),
        initial_state_covariance=np.ones((2, 2)),
        transition_matrices=np.eye(2),
        observation_matrices=obs_mat,
        observation_covariance=1.0,
        transition_covariance=trans_cov
    )
    
    state_means, _ = kf.filter(y.values)
    return state_means[:, 0], state_means[:, 1]