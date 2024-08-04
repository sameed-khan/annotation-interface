import {globSync} from 'glob';
import fs from 'fs';
import path from 'path';
import {InputOption} from 'rollup';

/**
 * This build script is a workaround for Vite not supporting Jinja2 templates.
 * The script RELIES on two assumptions: that the entry point HTML for a page matches that page's
 * directory name (i.e: front/pages/login entry point is login.html.jinja2).
 * The other assumption is that all Jinja2 includes are ADJACENT to the entry point file.
 */

const FRONT_DIR: string = 'front';
const DIST_DIR: string = 'dist';

function findJinja2Files(directory: string): string[] {
  return globSync(`${directory}/**/*.html.jinja2`);
}

export function processJinjaFile(filePath: string, includeList?: string[]): string[] {
  /**
   * Recursively process Jinja includes in a file. This function will:
   *  - Read the file content
   *  - regex to locate include statement
   *  - use path to return an Object with the entry point for vite
   * Ex: path = 'front/pages/login/login.html.jinja2'
   *    content = '...{% include "header.html.jinja2" %}...'
   *    output = {login: 'front/pages/login/login.html'}
   *
   * @param filePath: string - path to the Jinja2 file - MUST BE AN ENTRY POINT
   * @return returnList: string[] - complete list of included files to be bundled with entry point.
   */
  let returnList = includeList || [];
  let content: string = fs.readFileSync(filePath, 'utf-8');
  const includeRegex: RegExp = /{%\s*include\s*"([^"]+\.html\.jinja2)"(?:\s+with\s+context)?\s*%}/g;
  const matches: RegExpMatchArray[] = Array.from(content.matchAll(includeRegex));

  for (const match of matches) {
    const includePath: string = match[1];
    const fullIncludePath: string = path.join(path.dirname(filePath), includePath);
    returnList.push(fullIncludePath);
    returnList = [...returnList, ...processJinjaFile(fullIncludePath, returnList)];
  }

  return [filePath, ...new Set(returnList)];
}

export function convertIncludesToChunks(configInput: InputOption) {
  /**
   * @param configInput: InputOption - rollupOptions.input from Vite config
   * @return manualChunks: Record<string, string[]> - output.manualChunks config entry
   **/

  let processedInput: InputOption = {};
  if (typeof configInput === 'string') {
    processedInput = {
      [path.basename(configInput, path.extname(configInput))]: configInput,
    };
  } else if (Array.isArray(configInput)) {
    for (const input of configInput) {
      processedInput[path.basename(input, path.extname(input))] = input;
    }
  } else {
    processedInput = configInput;
  }

  let entryPoints: string[] = Object.values(processedInput);
  let manualChunks: Record<string, string[]> = Object.entries(processedInput).reduce(
    (acc, [key, value]) => {
      acc[key] = processJinjaFile(value);
      return acc;
    },
    {}
  );

  // entryPoints.reduce((acc, item) => {
  //   acc[item] = processJinjaFile(item);
  //   return acc;
  // }, {});

  return manualChunks;
}
