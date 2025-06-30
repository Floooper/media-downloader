import React from 'react';
import { ActionIcon, Tooltip } from '@mantine/core';
import { IconSun, IconMoon } from '@tabler/icons-react';
import { useTheme } from '../contexts/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <Tooltip label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
      <ActionIcon
        variant="subtle"
        size="lg"
        onClick={toggleTheme}
        sx={(theme) => ({
          color: theme.colorScheme === 'dark' ? theme.colors.yellow[4] : theme.colors.blue[6],
          '&:hover': {
            backgroundColor: theme.colorScheme === 'dark' 
              ? theme.colors.dark[5] 
              : theme.colors.gray[0],
          },
        })}
      >
        {theme === 'light' ? <IconMoon size={18} /> : <IconSun size={18} />}
      </ActionIcon>
    </Tooltip>
  );
};
