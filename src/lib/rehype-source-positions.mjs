/**
 * Preserve Markdown source ranges on rendered elements. Prism Studio uses
 * these markers to map an editor line to the matching rendered block.
 */
export function rehypeSourcePositions() {
  return (tree) => {
    const walk = (node) => {
      if (node?.type === 'element' && node.position?.start?.line) {
        node.properties ||= {};
        node.properties['data-source-start'] = String(node.position.start.line);
        node.properties['data-source-end'] = String(node.position.end?.line ?? node.position.start.line);
      }
      for (const child of node?.children ?? []) walk(child);
    };
    walk(tree);
  };
}
