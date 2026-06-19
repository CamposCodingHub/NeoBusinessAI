import { initializeApp, getApps, FirebaseApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";

// Configuração Firebase com validação rigorosa
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Validação rigorosa da configuração
const validateConfig = (): boolean => {
  const requiredFields: (keyof typeof firebaseConfig)[] = [
    'apiKey',
    'authDomain',
    'projectId',
    'storageBucket',
    'messagingSenderId',
    'appId'
  ];

  const missing = requiredFields.filter(
    (field) => !firebaseConfig[field] || firebaseConfig[field].trim() === ''
  );

  if (missing.length > 0) {
    console.error("❌ ERRO CRÍTICO: Firebase config incompleta");
    console.error("Campos faltando:", missing);
    console.error("\nPor favor, configure as variáveis de ambiente em .env.local");
    console.error("Use frontend/.env.example como referência");
    return false;
  }

  // Validações adicionais
  if (!firebaseConfig.apiKey || firebaseConfig.apiKey.length < 20) {
    console.error("❌ NEXT_PUBLIC_FIREBASE_API_KEY inválida");
    return false;
  }

  if (!firebaseConfig.projectId || !firebaseConfig.projectId.includes('-')) {
    console.error("❌ NEXT_PUBLIC_FIREBASE_PROJECT_ID inválido");
    return false;
  }

  return true;
};

// Inicialização segura com falha rápida
let app: FirebaseApp;

if (getApps().length === 0) {
  if (!validateConfig()) {
    throw new Error(
      "Firebase configuration is incomplete. Please check your .env.local file. " +
      "Required fields: NEXT_PUBLIC_FIREBASE_API_KEY, NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN, " +
      "NEXT_PUBLIC_FIREBASE_PROJECT_ID, NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET, " +
      "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID, NEXT_PUBLIC_FIREBASE_APP_ID"
    );
  }

  try {
    app = initializeApp(firebaseConfig);
    console.log("✅ Firebase initialized successfully");
    console.log(`📦 Project: ${firebaseConfig.projectId}`);
  } catch (error) {
    console.error("❌ Falha ao inicializar Firebase:", error);
    throw error;
  }
} else {
  app = getApps()[0];
}

export const auth = getAuth(app);
export const db = getFirestore(app);

// Debug info (apenas em desenvolvimento)
if (typeof window !== "undefined" && process.env.NODE_ENV === 'development') {
  console.log("🔧 Firebase config (development):", {
    projectId: firebaseConfig.projectId,
    authDomain: firebaseConfig.authDomain,
    hasApiKey: !!firebaseConfig.apiKey,
    apiURL: process.env.NEXT_PUBLIC_API_URL,
  });
}