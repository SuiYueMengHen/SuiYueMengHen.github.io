import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const query = `query { user(login:"SuiYueMengHen") { pinnedItems(first:6, types:REPOSITORY) { nodes { ... on Repository { nameWithOwner name description primaryLanguage { name } stargazerCount forkCount licenseInfo { spdxId } repositoryTopics(first:20) { nodes { topic { name } } } homepageUrl } } } } }`;
const response = JSON.parse(
  execFileSync('gh', ['api', 'graphql', '-f', `query=${query}`], {
    encoding: 'utf8',
  }),
);
if (response.errors || !response.data?.user?.pinnedItems)
  throw new Error('Unable to read pinned GitHub repositories');
const projects = response.data.user.pinnedItems.nodes;
const root = path.join(process.cwd(), 'src/content/projects');
const updates = new Map();
for (const file of fs
  .readdirSync(root)
  .filter((name) => /\.ya?ml$/.test(name))) {
  const source = fs
    .readFileSync(path.join(root, file), 'utf8')
    .replace(/^pinned:.*\n/gm, '')
    .replace(/^pinnedOrder:.*\n/gm, '');
  updates.set(file, source.trimEnd() + '\npinned: false\n');
}
const quote = (value) => JSON.stringify(value);
projects.forEach((repo, index) => {
  const file = `${repo.nameWithOwner.toLowerCase().replace('/', '--')}.yaml`;
  const previous = updates.get(file) || '';
  const preserved = (key) =>
    previous.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'))?.[1];
  const fields = [
    `repo: ${quote(repo.nameWithOwner)}`,
    `title: ${quote(repo.name)}`,
    `description: ${preserved('description') || quote(repo.description || '')}`,
    `language: ${quote(repo.primaryLanguage?.name || null)}`,
    `stars: ${repo.stargazerCount}`,
    `forks: ${repo.forkCount}`,
    `license: ${quote(repo.licenseInfo?.spdxId || null)}`,
    `topics: ${quote(repo.repositoryTopics.nodes.map((node) => node.topic.name))}`,
    `homepage: ${quote(repo.homepageUrl || null)}`,
    `featured: ${preserved('featured') || 'false'}`,
    `order: ${preserved('order') || '100'}`,
    ...['cover', 'coverAlt'].flatMap((key) =>
      preserved(key) ? [`${key}: ${preserved(key)}`] : [],
    ),
    `pinned: true`,
    `pinnedOrder: ${index}`,
    `syncedAt: ${quote(new Date().toISOString())}`,
    '',
  ];
  updates.set(file, fields.join('\n'));
});
for (const [file, source] of updates)
  fs.writeFileSync(path.join(root, file), source);
console.log(
  `Synced ${projects.length} pinned repositories; About Me selections preserved.`,
);
