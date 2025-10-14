# Component Documentation Example

## React/Vue/Angular Component Documentation

This example shows how to use Claude Code to document UI components comprehensively.

### Basic Component Documentation

```bash
> document the Button component with all its props and usage examples
```

#### Generated Output Example:

```typescript
/**
 * Button Component
 *
 * A reusable button component that supports multiple variants, sizes, and states.
 * Follows the design system guidelines and supports accessibility features.
 *
 * @component
 * @example
 * ```tsx
 * // Basic usage
 * <Button onClick={handleClick}>Click me</Button>
 *
 * // Primary variant with loading state
 * <Button variant="primary" loading={true}>
 *   Save Changes
 * </Button>
 *
 * // Full width button with icon
 * <Button fullWidth startIcon={<SaveIcon />}>
 *   Save Document
 * </Button>
 * ```
 */
interface ButtonProps {
  /**
   * The content to display inside the button
   */
  children: React.ReactNode;

  /**
   * Click event handler
   */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;

  /**
   * Visual style variant
   * @default 'default'
   */
  variant?: 'default' | 'primary' | 'secondary' | 'danger' | 'ghost';

  /**
   * Button size
   * @default 'medium'
   */
  size?: 'small' | 'medium' | 'large';

  /**
   * Whether the button should be disabled
   * @default false
   */
  disabled?: boolean;

  /**
   * Whether to show a loading spinner
   * @default false
   */
  loading?: boolean;

  /**
   * Whether the button should take full width of its container
   * @default false
   */
  fullWidth?: boolean;

  /**
   * Icon to display before the button text
   */
  startIcon?: React.ReactNode;

  /**
   * Icon to display after the button text
   */
  endIcon?: React.ReactNode;

  /**
   * HTML button type attribute
   * @default 'button'
   */
  type?: 'button' | 'submit' | 'reset';

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Accessibility label for screen readers
   */
  ariaLabel?: string;
}
```

### Storybook Documentation Generation

```bash
> generate Storybook stories for the Button component with all variants
```

#### Generated Storybook Example:

```javascript
import { Button } from './Button';
import { SaveIcon, DeleteIcon } from '../icons';

export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    docs: {
      description: {
        component: 'A versatile button component with multiple variants and states.'
      }
    }
  },
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['default', 'primary', 'secondary', 'danger', 'ghost'],
      description: 'Visual style variant',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' }
      }
    },
    size: {
      control: { type: 'select' },
      options: ['small', 'medium', 'large'],
      description: 'Button size',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'medium' }
      }
    }
  }
};

// Default story
export const Default = {
  args: {
    children: 'Button'
  }
};

// All variants
export const Variants = () => (
  <div style={{ display: 'flex', gap: '1rem' }}>
    <Button variant="default">Default</Button>
    <Button variant="primary">Primary</Button>
    <Button variant="secondary">Secondary</Button>
    <Button variant="danger">Danger</Button>
    <Button variant="ghost">Ghost</Button>
  </div>
);

// All sizes
export const Sizes = () => (
  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
    <Button size="small">Small</Button>
    <Button size="medium">Medium</Button>
    <Button size="large">Large</Button>
  </div>
);

// With icons
export const WithIcons = () => (
  <div style={{ display: 'flex', gap: '1rem' }}>
    <Button startIcon={<SaveIcon />}>Save</Button>
    <Button endIcon={<DeleteIcon />} variant="danger">Delete</Button>
  </div>
);

// States
export const States = () => (
  <div style={{ display: 'flex', gap: '1rem' }}>
    <Button>Normal</Button>
    <Button disabled>Disabled</Button>
    <Button loading>Loading</Button>
  </div>
);
```

### Component Library Documentation

```bash
> generate a complete component library documentation with usage guidelines
> create a design system documentation for all UI components
> document component accessibility features and ARIA attributes
```

### Markdown Documentation for Component Library

```bash
> generate README.md for the component library with installation and usage
```

#### Generated README Example:

```markdown
# UI Component Library

## Installation

\`\`\`bash
npm install @company/ui-components
\`\`\`

## Usage

\`\`\`jsx
import { Button, Card, Modal } from '@company/ui-components';

function App() {
  return (
    <Card>
      <Button variant="primary">Click me</Button>
    </Card>
  );
}
\`\`\`

## Available Components

### Buttons
- `Button` - Standard button with multiple variants
- `IconButton` - Button with only an icon
- `ButtonGroup` - Group multiple buttons together

### Form Elements
- `Input` - Text input field
- `Select` - Dropdown selection
- `Checkbox` - Checkbox input
- `Radio` - Radio button input
- `Switch` - Toggle switch

### Layout
- `Card` - Content container
- `Grid` - Responsive grid layout
- `Stack` - Vertical or horizontal stack

## Theming

Components support theming through CSS variables...
```

## Automation Commands

```bash
# Generate documentation for all components
> document all components in the src/components directory

# Update existing documentation
> update component documentation to match current props

# Generate usage examples
> create usage examples for all exported components

# Check documentation coverage
> find components without proper documentation
```