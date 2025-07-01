import userEvent from '@testing-library/user-event';

export function setup(jsx: React.ReactElement) {
  return {
    user: userEvent.setup(),
    ...render(jsx),
  };
}

export const keyboardShortcuts = {
  tab: '{Tab}',
  enter: '{Enter}',
  escape: '{Escape}',
  space: '{Space}',
  backspace: '{Backspace}',
  delete: '{Delete}',
  arrowLeft: '{ArrowLeft}',
  arrowRight: '{ArrowRight}',
  arrowUp: '{ArrowUp}',
  arrowDown: '{ArrowDown}',
  home: '{Home}',
  end: '{End}',
  pageUp: '{PageUp}',
  pageDown: '{PageDown}',
  selectAll: '{Control>}a{/Control}',
  copy: '{Control>}c{/Control}',
  paste: '{Control>}v{/Control}',
  cut: '{Control>}x{/Control}',
  undo: '{Control>}z{/Control}',
  redo: '{Control>}y{/Control}',
  save: '{Control>}s{/Control}',
};

export async function typeWithDelay(
  element: HTMLElement,
  text: string,
  delayMs = 100
) {
  for (const char of text) {
    await userEvent.type(element, char);
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
}

export async function dragAndDrop(
  source: HTMLElement,
  target: HTMLElement,
  options = {}
) {
  await userEvent.drag(source);
  await userEvent.drop(target, options);
}

export async function hoverElement(element: HTMLElement, duration = 0) {
  await userEvent.hover(element);
  if (duration > 0) {
    await new Promise((resolve) => setTimeout(resolve, duration));
    await userEvent.unhover(element);
  }
}

export async function tabThroughElements(
  container: HTMLElement,
  expectedTabStops: number
) {
  const tabPresses = Array(expectedTabStops).fill(keyboardShortcuts.tab);
  for (const press of tabPresses) {
    await userEvent.keyboard(press);
  }
}

export async function fillFormFields(
  form: HTMLElement,
  fields: Record<string, string>
) {
  for (const [name, value] of Object.entries(fields)) {
    const input = form.querySelector(`[name="${name}"]`);
    if (input) {
      await userEvent.type(input as HTMLElement, value);
    }
  }
}

export async function selectOption(
  select: HTMLElement,
  optionText: string | RegExp
) {
  await userEvent.selectOptions(select, optionText);
}

export async function uploadFile(
  input: HTMLElement,
  file: File | File[]
) {
  const files = Array.isArray(file) ? file : [file];
  const dataTransfer = {
    files,
    items: files.map((f) => ({
      kind: 'file',
      type: f.type,
      getAsFile: () => f,
    })),
    types: ['Files'],
  };

  await userEvent.upload(input, files, { dataTransfer });
}

export async function rightClick(element: HTMLElement) {
  await userEvent.pointer([
    { target: element },
    { keys: '[MouseRight]', target: element },
  ]);
}

export async function doubleClick(element: HTMLElement) {
  await userEvent.dblClick(element);
}

export async function pressKey(
  key: keyof typeof keyboardShortcuts,
  options = {}
) {
  await userEvent.keyboard(keyboardShortcuts[key], options);
}

export async function pasteText(element: HTMLElement, text: string) {
  await userEvent.click(element);
  await userEvent.paste(text);
}

export async function clearInput(element: HTMLElement) {
  await userEvent.clear(element);
}

export async function submitForm(form: HTMLElement) {
  const submitButton = form.querySelector('button[type="submit"]');
  if (submitButton) {
    await userEvent.click(submitButton);
  } else {
    await userEvent.keyboard(keyboardShortcuts.enter);
  }
}

export async function waitForAnimation(element: HTMLElement) {
  return new Promise<void>((resolve) => {
    element.addEventListener('animationend', () => resolve(), { once: true });
  });
}

export async function waitForTransition(element: HTMLElement) {
  return new Promise<void>((resolve) => {
    element.addEventListener('transitionend', () => resolve(), { once: true });
  });
}

// Example usage:
// const { user } = setup(<MyComponent />);
//
// test('form submission', async () => {
//   const form = screen.getByRole('form');
//   
//   await fillFormFields(form, {
//     email: 'test@example.com',
//     password: 'password123',
//   });
//   
//   await submitForm(form);
//   
//   expect(screen.getByText('Success')).toBeInTheDocument();
// });
