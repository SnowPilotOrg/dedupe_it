/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file was automatically generated by TanStack Router.
// You should NOT make any changes in this file as it will be overwritten.
// Additionally, you should also exclude this file from your linter and/or formatter to prevent it from being checked or modified.

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as DedupeImport } from './routes/dedupe'
import { Route as IndexImport } from './routes/index'

// Create/Update Routes

const DedupeRoute = DedupeImport.update({
  id: '/dedupe',
  path: '/dedupe',
  getParentRoute: () => rootRoute,
} as any)

const IndexRoute = IndexImport.update({
  id: '/',
  path: '/',
  getParentRoute: () => rootRoute,
} as any)

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/': {
      id: '/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof IndexImport
      parentRoute: typeof rootRoute
    }
    '/dedupe': {
      id: '/dedupe'
      path: '/dedupe'
      fullPath: '/dedupe'
      preLoaderRoute: typeof DedupeImport
      parentRoute: typeof rootRoute
    }
  }
}

// Create and export the route tree

export interface FileRoutesByFullPath {
  '/': typeof IndexRoute
  '/dedupe': typeof DedupeRoute
}

export interface FileRoutesByTo {
  '/': typeof IndexRoute
  '/dedupe': typeof DedupeRoute
}

export interface FileRoutesById {
  __root__: typeof rootRoute
  '/': typeof IndexRoute
  '/dedupe': typeof DedupeRoute
}

export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths: '/' | '/dedupe'
  fileRoutesByTo: FileRoutesByTo
  to: '/' | '/dedupe'
  id: '__root__' | '/' | '/dedupe'
  fileRoutesById: FileRoutesById
}

export interface RootRouteChildren {
  IndexRoute: typeof IndexRoute
  DedupeRoute: typeof DedupeRoute
}

const rootRouteChildren: RootRouteChildren = {
  IndexRoute: IndexRoute,
  DedupeRoute: DedupeRoute,
}

export const routeTree = rootRoute
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()

/* ROUTE_MANIFEST_START
{
  "routes": {
    "__root__": {
      "filePath": "__root.tsx",
      "children": [
        "/",
        "/dedupe"
      ]
    },
    "/": {
      "filePath": "index.tsx"
    },
    "/dedupe": {
      "filePath": "dedupe.tsx"
    }
  }
}
ROUTE_MANIFEST_END */