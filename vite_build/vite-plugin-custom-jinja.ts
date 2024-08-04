import {createFilter} from 'vite';
import type {Plugin, UserConfig, BuildOptions} from 'vite';
import type {InputOption, RollupOptions, OutputOptions} from 'rollup';
import path from 'path';
import {copyFile, rm, rename, access} from 'fs/promises';
import {convertIncludesToChunks} from './utils';

function configHasNecessaryProperties(config: UserConfig): config is UserConfig & {
  build: BuildOptions & {
    rollupOptions: RollupOptions & {input: InputOption};
  };
} {
  return !!config.build?.rollupOptions?.input;
}

export default function customJinjaPlugin(): Plugin {
  const filter = createFilter(['**/*.html.jinja2', '**/*.html']);
  let allFilesToProcess: string[];
  let processedJinjaFiles: string[];
  let config: any; // Fix this later

  return {
    name: 'custom-jinja-plugin',
    apply: 'build',

    // modify entry points to include jinja2 includes
    // produce .html files from .html.jinja2 files
    config: async (config, {}) => {
      if (!configHasNecessaryProperties(config)) return;

      const entryPoints = config.build.rollupOptions.input;
      const manualChunks = convertIncludesToChunks(entryPoints);
      allFilesToProcess = Object.values(manualChunks).flat();
      processedJinjaFiles = allFilesToProcess.map((filepath) => {
        return filepath.replace('.jinja2', '');
      });

      /**
       * entryPoints: { login: 'root/dir/login.html.jinja2' } -->
       * manualChunks: { login: ['root/dir/login.html.jinja2', 'root/dir/login_child.html.jinja2'] }
       * newEntryPoints: { login: 'root/dir/login.html', login_child: 'root/dir/login_child.html' }
       */
      config.build.rollupOptions.input = allFilesToProcess.reduce((acc, item) => {
        acc[path.basename(item).split('.')[0]] = item.replace('.jinja2', '');
        return acc;
      }, {});

      /**
       * { login: ['root/dir/login.html.jinja2', 'root/dir/login_child.html.jinja2'] } -->
       * { login: ['root/dir/login.html', 'root/dir/login_child.html'] }
       */
      let manualChunksJinjaExtRemoved = Object.entries(manualChunks).reduce((acc, [key, value]) => {
        acc[key] = value.map((item) => item.replace('.jinja2', ''));
        return acc;
      }, {});

      config.build.rollupOptions.output ??= {};
      (<OutputOptions>config.build.rollupOptions.output).manualChunks = manualChunksJinjaExtRemoved;
    },

    configResolved: (resolvedConfig) => {
      config = resolvedConfig;
      console.log(`Rollup Options: ${JSON.stringify(config.build.rollupOptions, null, 2)}`);
    },

    // Copy all the .html.jinja2 files to .html files
    buildStart: async () => {
      await Promise.all(
        allFilesToProcess.map(async (filepath) => {
          const toPath = filepath.replace('.jinja2', '');
          await copyFile(filepath, toPath);
        })
      );
    },

    closeBundle: async () => {
      await Promise.all(
        processedJinjaFiles.map(async (filepath) => {
          // Rename all the former .html.jinja2 files in the output folder back to .html.jinja2
          // Ex: /project/front/pages/login/login.html --> /project/front/../dist/login/login.html
          const outputtedPath = filepath.replace(
            config.root,
            path.join(config.root, config.build.outDir)
          );
          const jinjaRenamedPath = outputtedPath.replace('.html', '.html.jinja2');

          try {
            await access(outputtedPath);
            await rename(outputtedPath, jinjaRenamedPath);
          } catch (error) {}

          // Delete all the .html copies we generated from .html.jinja2 files
          try {
            access(filepath);
            await rm(filepath);
          } catch (error) {}
        })
      );
    },
  };
}
