export interface CommandItem {
  id: string;
  name: string;
  description?: string;
  icon?: React.ReactNode;
  shortcut?: string[];
  category?: string;
  action: () => void;
}

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  commands: CommandItem[];
  placeholder?: string;
  maxResults?: number;
}
