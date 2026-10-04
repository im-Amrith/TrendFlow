import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyDFRvXLb2FVYym1ixfPEr-5ooej0C_-CUo",
  authDomain: "trendflow-761ac.firebaseapp.com",
  projectId: "trendflow-761ac",
  storageBucket: "trendflow-761ac.firebasestorage.app",
  messagingSenderId: "370492409354",
  appId: "1:370492409354:web:13b86b4d1c2312398501f3",
  measurementId: "G-J29RMLMRB8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();
