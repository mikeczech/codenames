# Secret Agents AI

This project presents a web-based, multiplayer online game inspired by Codenames, integrating [word embeddings](https://explosion.ai/blog/floret-vectors) to assist players in generating relevant clues. It combines classic word association gameplay with a touch of AI, aiming for a more intuitive and engaging experience.

<p align="center">
  <img src="images/example.gif" />
</p>

## Status

This game is currently in a work-in-progress state and not yet fully developed, with some rough edges still present. While it offers a solid foundation of the basic gameplay, be aware that it lacks several features you might expect from a typical Codenames game.

## Getting Started

To begin working on the application, clone this repository and then open the root directory of this repo in your terminal.

Make sure you have the latest version of [Poetry](https://python-poetry.org) installed.

Install dependencies and initialize the database:

    make install && make init-db

Run the backend:

    make run-backend

Run the frontend:

    make run-frontend

Having both the backend and frontend running in the background, one can access the application on [http://localhost:3000](http://localhost:3000).

Run the tests:

    make run-tests

Format the code:

    make format
