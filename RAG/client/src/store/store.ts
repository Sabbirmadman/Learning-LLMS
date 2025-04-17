import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import selectionReducer from './slices/selectionSlice';
import { authApi } from '../lib/redux/api/authApi';
import { fileApi } from '../lib/redux/api/fileApi';
import { scrapeApi } from '../lib/redux/api/scrapeApi';
import {chatApi } from '../lib/redux/api/chatApis';
import { authMiddleware } from '@/lib/redux/middleware/authMiddleware';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    selection: selectionReducer,
    [authApi.reducerPath]: authApi.reducer,
    [fileApi.reducerPath]: fileApi.reducer,
    [scrapeApi.reducerPath]: scrapeApi.reducer,
    [chatApi.reducerPath]: chatApi.reducer,

  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      authApi.middleware,
      fileApi.middleware,
      scrapeApi.middleware,
      chatApi.middleware,
      authMiddleware
    ),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;