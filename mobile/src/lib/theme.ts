import { Platform } from 'react-native';

export const colors = {
  forest: '#1F3D2B',
  leaf: '#3E7C4F',
  sage: '#DCE7D6',
  cream: '#F6F2E7',
  paper: '#FFFDF7',
  terracotta: '#B9552E',
  terracottaSoft: '#F6E1D6',
  ink: '#1B211C',
  muted: '#667066',
  line: '#E4DFD0',
  white: '#FFFFFF',
};

// A serif for headings gives the app the feel of a gardening journal
export const serif = Platform.select({ ios: 'Georgia', android: 'serif', default: 'Georgia, serif' });

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 };
export const radius = { sm: 8, md: 14, lg: 22 };
