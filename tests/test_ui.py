#!/usr/bin/env python3
"""
Tests for UI components

Unit tests for status display and other UI elements.
"""

import unittest
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.status_display import StatusDisplay


class TestStatusDisplay(unittest.TestCase):
    """Test the StatusDisplay class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.status = StatusDisplay()
    
    def test_status_display_creation(self):
        """Test that status display can be created."""
        self.assertIsInstance(self.status, StatusDisplay)
        self.assertEqual(self.status.frame_count, 0)
        self.assertTrue(self.status.show_debug)
        self.assertTrue(self.status.show_coordinates)
        self.assertFalse(self.status.show_fps)
    
    def test_update_frame_count(self):
        """Test frame count updating."""
        initial_count = self.status.frame_count
        self.status.update_frame_count()
        self.assertEqual(self.status.frame_count, initial_count + 1)
        
        # Test multiple updates
        for i in range(5):
            self.status.update_frame_count()
        self.assertEqual(self.status.frame_count, initial_count + 6)
    
    def test_toggle_debug(self):
        """Test toggling debug display."""
        initial_state = self.status.show_debug
        self.status.toggle_debug()
        self.assertEqual(self.status.show_debug, not initial_state)
        
        # Toggle back
        self.status.toggle_debug()
        self.assertEqual(self.status.show_debug, initial_state)
    
    def test_toggle_coordinates(self):
        """Test toggling coordinate display."""
        initial_state = self.status.show_coordinates
        self.status.toggle_coordinates()
        self.assertEqual(self.status.show_coordinates, not initial_state)
        
        # Toggle back
        self.status.toggle_coordinates()
        self.assertEqual(self.status.show_coordinates, initial_state)
    
    def test_toggle_fps(self):
        """Test toggling FPS display."""
        initial_state = self.status.show_fps
        self.status.toggle_fps()
        self.assertEqual(self.status.show_fps, not initial_state)
        
        # Toggle back
        self.status.toggle_fps()
        self.assertEqual(self.status.show_fps, initial_state)
    
    def test_color_properties(self):
        """Test that color properties are set correctly."""
        self.assertEqual(self.status.info_color, (255, 255, 255))
        self.assertEqual(self.status.debug_color, (200, 200, 200))
        self.assertEqual(self.status.warning_color, (255, 255, 0))
        self.assertEqual(self.status.error_color, (255, 100, 100))


class MockConsole:
    """Mock console for testing UI rendering without tcod dependency."""
    
    def __init__(self, width=80, height=50):
        self.width = width
        self.height = height
        self.printed_chars = []
    
    def print(self, x, y, text, fg=None, bg=None):
        """Mock print method that records what was printed."""
        self.printed_chars.append({
            'x': x, 'y': y, 'text': text, 'fg': fg, 'bg': bg
        })


class TestStatusDisplayRendering(unittest.TestCase):
    """Test the rendering methods of StatusDisplay (without actual tcod)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.status = StatusDisplay()
        self.console = MockConsole(80, 25)
    
    def test_render_status_bar_basic(self):
        """Test basic status bar rendering."""
        self.status.show_debug = True  # Enable debug mode to show status bar
        self.status.render_status_bar(self.console, 10, 20)

        # Should have printed something (floating container with borders and content)
        self.assertGreater(len(self.console.printed_chars), 0)

        # Check that it printed in the floating container area (y=1 for top container)
        # Look for content in the top area of the screen
        top_area_prints = [p for p in self.console.printed_chars if p['y'] <= 5]
        self.assertGreater(len(top_area_prints), 0)
    
    def test_render_status_bar_disabled(self):
        """Test status bar rendering when debug is disabled."""
        self.status.show_debug = False
        self.status.render_status_bar(self.console, 10, 20)
        
        # Should not have printed anything
        self.assertEqual(len(self.console.printed_chars), 0)
    
    def test_render_help_text(self):
        """Test help text rendering."""
        self.status.render_help_text(self.console)
        
        # Should have printed help text
        self.assertGreater(len(self.console.printed_chars), 0)
        
        # Help text should be near the bottom
        help_prints = [p for p in self.console.printed_chars if p['y'] > self.console.height - 5]
        self.assertGreater(len(help_prints), 0)
    
    def test_render_message(self):
        """Test message rendering."""
        self.status.render_message(self.console, "Test message", 5, 10)
        
        # Should have printed the message
        self.assertEqual(len(self.console.printed_chars), 1)
        
        printed = self.console.printed_chars[0]
        self.assertEqual(printed['x'], 5)
        self.assertEqual(printed['y'], 10)
        self.assertEqual(printed['text'], "Test message")
    
    def test_render_centered_message(self):
        """Test centered message rendering."""
        message = "Center me"
        self.status.render_centered_message(self.console, message, 15)
        
        # Should have printed the message
        self.assertEqual(len(self.console.printed_chars), 1)
        
        printed = self.console.printed_chars[0]
        expected_x = (self.console.width - len(message)) // 2
        self.assertEqual(printed['x'], expected_x)
        self.assertEqual(printed['y'], 15)
        self.assertEqual(printed['text'], message)


if __name__ == "__main__":
    unittest.main()
