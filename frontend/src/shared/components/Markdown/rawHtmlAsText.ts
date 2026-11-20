interface MdNode {
  type: string
  value?: string
  children?: MdNode[]
}

function walk(node: MdNode): void {
  if (node.type === 'html') node.type = 'text'
  node.children?.forEach(walk)
}

/**
 * A remark plugin that turns raw HTML into plain text, so `<script>alert(1)</script>` in a page
 * shows as those characters instead of being dropped or run (criterion 60).
 */
export function rawHtmlAsText() {
  return (tree: MdNode) => walk(tree)
}
