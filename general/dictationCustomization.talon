mode: dictation
not app: vscode

-

#Match cursorless syntax
format <user.formatters> at this: user.formatters_reformat_selection(formatters)

question work: "?"

^left$: 
    key(ctrl-backspace)

^iter$:
    key(enter)
    