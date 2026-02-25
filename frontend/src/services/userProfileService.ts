import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface UserProfile {
  name: string;
  avatarUrl?: string;
  location?: {
    address?: string;
    latitude?: number;
    longitude?: number;
  };
  city?: string;
  region?: string;
  country?: string;
  profession?: string;
}

export const getUserProfile = async (): Promise<UserProfile | null> => {
  try {
    const response = await axios.get<UserProfile>(`${API_BASE_URL}/user-profile`);
    return response.data;
  } catch (error) {
    console.error('Error loading user profile:', error);
    return null;
  }
};
