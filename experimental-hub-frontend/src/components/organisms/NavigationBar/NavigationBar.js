import { NavLink } from "react-router-dom";
import "./NavigationBar.css";

function NavigationBar() {
  return (
    <div className="headerContainer">
      <NavLink className="pageNavigation" to="/">
        Home
      </NavLink>
      <NavLink className="pageNavigation" to="/sessionOverview">
        Session Overview
      </NavLink>
      <NavLink className="pageNavigation" to="/watchingRoom">
        Watching Room
      </NavLink>
      <NavLink className="pageNavigation" to="/postProcessingRoom">
        Post-Processing Room
      </NavLink>
    </div>
  );
}

export default NavigationBar;
