const fs = require('node:fs/promises');
const path = require('node:path');
const {compile} = require('json-schema-to-typescript');
async function main() {
  const check = process.argv.includes('--check');
  const root = path.resolve(__dirname, '..');
  const targets = [['dashboard-envelope', 'contracts'], ['evidence-cache', 'evidence-cache'], ['run-command', 'commands'], ['create-run','create-run'], ['scenario-request','scenario-request'], ['live-market-context','live-market-context'], ['live-audio-sentiment','live-audio-sentiment']];
  for (const [schemaName, outputName] of targets) {
    const schema = JSON.parse(await fs.readFile(path.join(root, 'contracts/generated', schemaName + '.schema.json'), 'utf8'));
    const output = await compile(schema, schema.title, {bannerComment:'/* Generated from schema 2 serialization output. Root-owned; do not edit. */', additionalProperties:false});
    const directory = path.join(root, 'frontend/src/generated');
    const filename = path.join(directory, outputName + '.ts');
    if (check) {
      if (await fs.readFile(filename, 'utf8') !== output) throw new Error('Generated TypeScript drift: ' + outputName);
    } else { await fs.mkdir(directory, {recursive:true}); await fs.writeFile(filename, output); }
  }
  console.log(check ? 'Generated TypeScript drift check passed' : 'Generated schema 2 TypeScript');
}
main().catch(error => {console.error(error.message); process.exitCode=1;});
