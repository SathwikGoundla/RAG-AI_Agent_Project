declare module 'pdf-parse' {
  interface Options {
    pagerender?: (pageData: any) => string | Promise<string>;
    max?: number;
    version?: string;
  }

  interface Output {
    numpages: number;
    numrender: number;
    info: any;
    metadata: any;
    text: string;
    version: string;
  }

  function PDFParse(dataBuffer: Buffer | Uint8Array, options?: Options): Promise<Output>;
  export = PDFParse;
}
