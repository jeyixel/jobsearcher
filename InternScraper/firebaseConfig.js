import { initializeApp } from "firebase/app";
import { initializeAuth, getReactNativePersistence } from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBkblhh5ncLb9yuWXiIy9hBrHnpkYy0ZEs",
  authDomain: "internsearch-a124f.firebaseapp.com",
  projectId: "internsearch-a124f",
  storageBucket: "internsearch-a124f.firebasestorage.app",
  messagingSenderId: "520036392238",
  appId: "1:520036392238:web:060ec66072d375e5fbeebf"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Auth with persistence (Optional, but recommended for mobile)
const auth = initializeAuth(app, {
  persistence: getReactNativePersistence(AsyncStorage)
});

export { app, auth };