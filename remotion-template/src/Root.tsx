import "./index.css";
import { Example } from "./Example";

// Every video is a folder in src/ with an index.tsx exporting its <Composition>.
// Register new videos here: one import and one element.
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Example />
    </>
  );
};
