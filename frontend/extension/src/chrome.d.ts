// Minimal ambient declaration for the Chrome extension API when @types/chrome is not installed.
// If you install `@types/chrome`, this file can be removed.
declare namespace chrome {
  const runtime: any;
  const storage: {
    local: {
      get(keys: any, callback: (items: any) => void): void;
      set(items: any, callback?: () => void): void;
      remove(keys: string[] | string, callback?: () => void): void;
    }
  };
}

declare const chrome: typeof chrome;
