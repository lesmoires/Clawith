declare module 'react-dom/client' {
  import { ReactNode } from 'react';
  export function createRoot(container: Element | DocumentFragment): {
    render(children: ReactNode): void;
    unmount(): void;
  };
}

declare module 'react-dom' {
  export * from 'react-dom/client';
  export function createPortal(children: React.ReactNode, container: Element | DocumentFragment): React.ReactNode;
  export function flushSync<T>(fn: () => T): T;
}
