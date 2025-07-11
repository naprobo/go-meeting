<template>
  <div v-html="highlightedDiff"></div>
</template>

<script>
import DiffMatchPatch from "diff-match-patch";

export default {
  props: ["oldText", "newText"],
  computed: {
    highlightedDiff() {
      const dmp = new DiffMatchPatch();
      const diffs = dmp.diff_main(this.oldText, this.newText);
      dmp.diff_cleanupSemantic(diffs);

      return diffs
        .map(([type, text]) => {
          if (type === 1) return `<span style="color: green;">✅ ${text}</span>`;
          if (type === -1) return `<span style="color: red;">❌ ${text}</span>`;
          return `<span>${text}</span>`;
        })
        .join("");
    }
  }
};
</script>

