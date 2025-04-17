import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SelectedFile {
  id: string;
  filename: string;
  size: number;
  type: string;
  createdAt: string;
}

export interface SelectedUrl {
  id: string;
  url: string;
  createdAt: string;
}

interface SelectionState {
  selectedFileIds: SelectedFile[];
  selectedUrlIds: SelectedUrl[];
}

const initialState: SelectionState = {
  selectedFileIds: [],
  selectedUrlIds: [],
};

export const selectionSlice = createSlice({
  name: 'selection',
  initialState,
  reducers: {
    toggleFileSelection: (state, action: PayloadAction<SelectedFile>) => {
      const fileToToggle = action.payload;
      const index = state.selectedFileIds.findIndex(file => file.id === fileToToggle.id);
      
      if (index >= 0) {
        state.selectedFileIds.splice(index, 1);
      } else {
        state.selectedFileIds.push(fileToToggle);
      }
    },
    selectFiles: (state, action: PayloadAction<SelectedFile[]>) => {
      state.selectedFileIds = action.payload;
    },
    clearFileSelection: (state) => {
      state.selectedFileIds = [];
    },
    toggleUrlSelection: (state, action: PayloadAction<SelectedUrl>) => {
      const urlToToggle = action.payload;
      const index = state.selectedUrlIds.findIndex(url => url.id === urlToToggle.id);
      
      if (index >= 0) {
        state.selectedUrlIds.splice(index, 1);
      } else {
        state.selectedUrlIds.push(urlToToggle);
      }
    },
    selectUrls: (state, action: PayloadAction<SelectedUrl[]>) => {
      state.selectedUrlIds = action.payload;
    },
    clearUrlSelection: (state) => {
      state.selectedUrlIds = [];
    },
    clearAllSelections: (state) => {
      state.selectedFileIds = [];
      state.selectedUrlIds = [];
    }
  },
});

export const {
  toggleFileSelection,
  selectFiles,
  clearFileSelection,
  toggleUrlSelection,
  selectUrls,
  clearUrlSelection,
  clearAllSelections,
} = selectionSlice.actions;

export default selectionSlice.reducer;