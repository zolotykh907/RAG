import {Routes, Route} from 'react-router-dom';
import Introduction from '../sections/Introduction';
import Description from '../sections/Description';
import Architecture from '../sections/Architecture';
import Technologies from '../sections/Technologies';
import Installation from '../sections/Installation';
import Usage from '../sections/Usage';
import Api from '../sections/Api';
import Testing from '../sections/Testing';
import Posts from '../sections/Posts';
import Flip from '../sections/Flip'

const MainPanel = () => (
  <main className="main-content">
    <Routes>
      <Route path="*" element={<Introduction />} />
      <Route path="/introduction" element={<Introduction />} />
      <Route path="/description" element={<Description />} />
      <Route path="/architecture" element={<Architecture />} />
      <Route path="/technologies" element={<Technologies />} />
      <Route path="/installation" element={<Installation />} />
      <Route path="/usage" element={<Usage />} />
      <Route path="/api" element={<Api />} />
      <Route path="/testing" element={<Testing />} />
      < Route path="/posts" element={<Posts />} />
      < Route path="/flip" element={<Flip />} />
    </Routes>
  </main>
);

export default MainPanel;