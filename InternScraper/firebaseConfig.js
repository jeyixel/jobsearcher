// services/firebase.js (or wherever you keep this file)

import auth from '@react-native-firebase/auth';
import firestore from '@react-native-firebase/firestore';
import messaging from '@react-native-firebase/messaging';

// That's it!
// We do NOT need initializeApp() or firebaseConfig.
// The library automatically reads your keys from google-services.json

export { auth, firestore, messaging };