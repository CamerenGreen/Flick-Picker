// Minimal JSX declarations to satisfy TypeScript when Preact types aren't available yet.
// If you have full Preact types installed, you can remove this file.
declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}
