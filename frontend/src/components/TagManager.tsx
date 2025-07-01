import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  TextField,
  Button,
  Grid,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { Tag } from '../types/api';
import * as api from '../services/api';
import logger from '../services/logging';

const TagManager: React.FC = () => {
  const [tags, setTags] = useState<Tag[]>([]);
  const [newTagName, setNewTagName] = useState('');
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [editingName, setEditingName] = useState('');

  useEffect(() => {
    fetchTags();
  }, []);

  const fetchTags = async () => {
    try {
      const fetchedTags = await api.getTags();
      setTags(fetchedTags);
    } catch (error) {
      logger.error('Failed to fetch tags', error);
    }
  };

  const handleCreateTag = async () => {
    if (!newTagName.trim()) return;

    try {
      await api.createTag(newTagName);
      setNewTagName('');
      fetchTags();
    } catch (error) {
      logger.error('Failed to create tag', error);
    }
  };

  const handleDeleteTag = async (id: number) => {
    try {
      await api.deleteTag(id);
      fetchTags();
    } catch (error) {
      logger.error('Failed to delete tag', error);
    }
  };

  const handleStartEdit = (tag: Tag) => {
    setEditingTag(tag);
    setEditingName(tag.name);
  };

  const handleCancelEdit = () => {
    setEditingTag(null);
    setEditingName('');
  };

  const handleSaveEdit = async () => {
    if (!editingTag || !editingName.trim()) return;

    try {
      await api.updateTag(editingTag.id, editingName);
      setEditingTag(null);
      setEditingName('');
      fetchTags();
    } catch (error) {
      logger.error('Failed to update tag', error);
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Tag Manager
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="New Tag Name"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleCreateTag()}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Button
            variant="contained"
            onClick={handleCreateTag}
            disabled={!newTagName.trim()}
          >
            Create Tag
          </Button>
        </Grid>
      </Grid>

      <List>
        {tags.map((tag) => (
          <ListItem key={tag.id}>
            {editingTag?.id === tag.id ? (
              <>
                <TextField
                  fullWidth
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSaveEdit()}
                />
                <ListItemSecondaryAction>
                  <IconButton edge="end" onClick={handleSaveEdit}>
                    <SaveIcon />
                  </IconButton>
                  <IconButton edge="end" onClick={handleCancelEdit}>
                    <CancelIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </>
            ) : (
              <>
                <ListItemText primary={tag.name} />
                <ListItemSecondaryAction>
                  <IconButton edge="end" onClick={() => handleStartEdit(tag)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton edge="end" onClick={() => handleDeleteTag(tag.id)}>
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </>
            )}
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default TagManager;
