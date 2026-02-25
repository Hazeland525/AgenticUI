import axios from 'axios';
import { UIResponse } from '../types/schema';

const API_BASE_URL = 'http://localhost:8000/api';

export interface SaveRequest {
  question: string;
  uiSchema: UIResponse;
  videoTime?: number;
}

export interface SavedItem {
  id: number;
  question: string;
  uiSchema: UIResponse;
  videoTime?: number;
  timestamp: string;
}

export const saveItem = async (request: SaveRequest): Promise<number> => {
  try {
    const response = await axios.post<{ id: number }>(
      `${API_BASE_URL}/save`,
      request
    );
    return response.data.id;
  } catch (error) {
    console.error('Error saving item:', error);
    throw error;
  }
};

export const getLibrary = async (): Promise<SavedItem[]> => {
  try {
    const response = await axios.get<SavedItem[]>(`${API_BASE_URL}/library`);
    return response.data;
  } catch (error) {
    console.error('Error getting library:', error);
    throw error;
  }
};

export const deleteItem = async (itemId: number): Promise<void> => {
  try {
    await axios.delete(`${API_BASE_URL}/library/${itemId}`);
  } catch (error) {
    console.error('Error deleting item:', error);
    throw error;
  }
};

