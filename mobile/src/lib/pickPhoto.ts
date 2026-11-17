import { Alert, Platform } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

import type { Photo } from './api';

const pickerOptions: ImagePicker.ImagePickerOptions = {
  mediaTypes: ['images'],
  quality: 0.7, // also turns iPhone HEIC photos into JPEG
  allowsEditing: true,
  aspect: [1, 1],
};

function toPhoto(result: ImagePicker.ImagePickerResult): Photo | null {
  if (result.canceled || !result.assets?.length) return null;
  const asset = result.assets[0];
  return { uri: asset.uri, name: asset.fileName ?? 'photo.jpg', type: asset.mimeType ?? 'image/jpeg' };
}

async function fromLibrary(): Promise<Photo | null> {
  return toPhoto(await ImagePicker.launchImageLibraryAsync(pickerOptions));
}

async function fromCamera(): Promise<Photo | null> {
  const permission = await ImagePicker.requestCameraPermissionsAsync();
  if (!permission.granted) {
    Alert.alert('Camera is off', 'Allow Rootly to use the camera in your phone settings to take a photo.');
    return null;
  }
  return toPhoto(await ImagePicker.launchCameraAsync(pickerOptions));
}

/** Asks "Take photo or choose one?" and returns the photo, or null if cancelled. */
export function pickPhoto(): Promise<Photo | null> {
  if (Platform.OS === 'web') return fromLibrary();
  return new Promise((resolve) => {
    Alert.alert('Add a photo', undefined, [
      { text: 'Take photo', onPress: () => fromCamera().then(resolve, () => resolve(null)) },
      { text: 'Choose from library', onPress: () => fromLibrary().then(resolve, () => resolve(null)) },
      { text: 'Cancel', style: 'cancel', onPress: () => resolve(null) },
    ], { cancelable: true, onDismiss: () => resolve(null) });
  });
}
