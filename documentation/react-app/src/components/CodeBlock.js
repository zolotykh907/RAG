import React from "react";
import { Highlight, themes } from "prism-react-renderer";

const CodeBlock = ({ children, language = "bash" }) => (
  <Highlight code={children.trim()} language={language} theme={themes.github}>
    {({ className, style, tokens, getLineProps, getTokenProps }) => (
      <pre
        className={className}
        style={{
          ...style,
          padding: "16px",
          borderRadius: "8px",
          margin: "12px 0",
          fontSize: "14px",
          overflowX: "auto",
        }}
      >
        {tokens.map((line, i) => (
          <div key={i} {...getLineProps({ line })}>
            {line.map((token, key) => (
              <span key={key} {...getTokenProps({ token })} />
            ))}
          </div>
        ))}
      </pre>
    )}
  </Highlight>
);

export default CodeBlock;
