import { createContext } from 'react';
import { Theme } from '@mui/material/styles';
import { darkTheme } from './themes';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

export const ThemeContext = createContext<ThemeContextType>({
  theme: darkTheme,
  toggleTheme: () => {},
});
