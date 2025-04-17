import { useDispatch, useSelector } from 'react-redux';
import { 
  loginSuccess, 
  loginFailure, 
  registerSuccess, 
  registerFailure,
  logout as logoutAction
} from '../store/slices/authSlice';
import { useLoginMutation, useRegisterMutation } from '../lib/redux/api/authApi';
import { RootState } from '@/store/store';

interface SignupData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

interface LoginData {
  email: string;
  password: string;
}

export const useAuth = () => {
  const dispatch = useDispatch();
  // Get authentication state from Redux store
  const { token } = useSelector((state: RootState) => state.auth);
  const isAuthenticated = !!token;
  
  // Use RTK Query mutations
  const [loginUser, { isLoading: isLoginLoading }] = useLoginMutation();
  const [registerUser, { isLoading: isRegisterLoading }] = useRegisterMutation();
  
  const isLoading = isLoginLoading || isRegisterLoading;

  const signup = async (userData: SignupData) => {
    try {
      const data = await registerUser(userData).unwrap();
      
      // Save token to localStorage
      localStorage.setItem('token', data.token);
      
      dispatch(registerSuccess({
        user: {
          email: userData.email,
          first_name: userData.first_name,
          last_name: userData.last_name,
          id: data.userId
        },
        token: data.token
      }));

      return data;
    } catch (error) {
      dispatch(registerFailure(error instanceof Error ? error.message : 'Unknown error occurred'));
      throw error;
    }
  };

  const login = async (loginData: LoginData) => {
    try {
      const data = await loginUser(loginData).unwrap();
      
      // Save token to localStorage
      localStorage.setItem('token', data.token);
      
      dispatch(loginSuccess({
        user: {
          email: loginData.email,
          id: data.userId,
          first_name: data.first_name,
          last_name: data.last_name
        },
        token: data.token
      }));

      return data;
    } catch (error) {
      dispatch(loginFailure(error instanceof Error ? error.message : 'Unknown error occurred'));
      throw error;
    }
  };

  const logout = () => {
    dispatch(logoutAction());
    localStorage.removeItem('token');
  };

  return {
    signup,
    login,
    logout,
    isLoading,
    isAuthenticated
  };
};