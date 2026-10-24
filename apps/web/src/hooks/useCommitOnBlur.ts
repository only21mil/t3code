import { type ChangeEvent, type KeyboardEvent, useRef, useState } from "react";

export function useCommitOnBlur(value: string, onCommit: (next: string) => void) {
  const [draft, setDraft] = useState<string | null>(null);
  // `value` can lag a pending save, so only an edit in this focus session decides whether to commit.
  const editedSinceFocus = useRef(false);

  return {
    value: draft ?? value,
    onChange: (event: ChangeEvent<HTMLInputElement>) => {
      editedSinceFocus.current = true;
      setDraft(event.target.value);
    },
    onFocus: () => {
      editedSinceFocus.current = false;
      setDraft(value);
    },
    onBlur: () => {
      const next = draft ?? value;
      const edited = editedSinceFocus.current;
      editedSinceFocus.current = false;
      setDraft(null);
      if (edited) {
        onCommit(next);
      }
    },
    onKeyDown: (event: KeyboardEvent<HTMLInputElement>) => {
      if (event.nativeEvent.isComposing || event.keyCode === 229) return;
      if (event.key === "Enter") {
        event.preventDefault();
        (event.target as HTMLInputElement).blur();
      }
    },
  };
}
