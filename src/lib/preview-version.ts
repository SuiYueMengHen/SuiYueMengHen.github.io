import { createHash } from 'node:crypto';

const text = (value: unknown) => value == null ? '' : String(value);
const flag = (value: unknown) => value ? 'true' : 'false';
const digest = (parts: string[]) => createHash('sha256').update(parts.join('\u001f')).digest('hex');

export function articlePreviewVersion(data: Record<string, any>, body = ''): string {
  return digest([
    text(data.title), text(data.description), text(data.category),
    (data.tags || []).map(text).join('\u001e'), text(data.collection), text(data.collectionOrder),
    flag(data.featured), flag(data.draft), text(data.canonical),
    flag(data.autoNumbering ?? true), flag(data.showContents ?? true), flag(data.showSideToc ?? true),
    body.replace(/\r\n/g, '\n').trim(),
  ]);
}

export function projectPreviewVersion(data: Record<string, any>): string {
  return digest([
    text(data.repo), text(data.title), text(data.description),
    (data.topics || []).map(text).join('\u001e'), text(data.homepage),
    text(data.cover), text(data.coverAlt), flag(data.featured), text(data.order),
  ]);
}

export function collectionPreviewVersion(data: Record<string, any>): string {
  return digest([
    text(data.title), text(data.description), text(data.subtitle), text(data.volume),
    text(data.status), flag(data.featured), text(data.order), text(data.cover), text(data.coverAlt),
  ]);
}

export function categoryPreviewVersion(names: string[]): string {
  return digest([[...new Set(names.map(text).filter(Boolean))].sort().join('\u001e')]);
}
