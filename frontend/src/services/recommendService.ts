import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface RecommendedPlace {
  name: string;
  placeId?: string;
  placeUrl?: string;
  address?: string;
  location?: { latitude?: number; longitude?: number };
  rating?: number;
  priceLevel?: string;
  photoUri?: string;
}

export interface RecommendResponse {
  places: RecommendedPlace[];
  reasoning: string;
  verbalSummary?: string;
}

export const recommend = async (message: string): Promise<RecommendResponse> => {
  const response = await axios.post<RecommendResponse>(
    `${API_BASE_URL}/recommend`,
    { message }
  );
  return response.data;
};
