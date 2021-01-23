import React from "react";
import {
  BrowserRouter as Router,
  Switch,
  Route,
  useParams
} from "react-router-dom";

export default function App() {
  return (
    <Router>
      <div>
        <Switch>
          <Route path="/:id">
            <Game />
          </Route>
          <Route path="/">
            <Create />
          </Route>
        </Switch>
      </div>
    </Router>
  );
}

function Create() {
  return <h2>Create a Game</h2>
}

function Game() {
  const { id } = useParams();
  return (
    <div>
      <h2>Game: {id}</h2>
      <div>
        <div>
          0
          1
          2
        </div>
        <div>
          0
          1
          2
        </div>
        <div>
          0
          1
          2
        </div>
      </div>
    </div>
  );
}
