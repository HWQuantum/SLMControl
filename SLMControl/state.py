"""This module contains an implementation of the state of the SLMControl program
"""

from uuid import UUID, uuid4


class SLMState:
    def __init__(self):
        # the minimal data conforming to the specs
        self._data = {"screens": {}, "views": {}, "patterns": {}}

    def get_screen_by_uuid(self, u: UUID) -> dict:
        """Get a screen by its UUID, giving an error if it can't be found
        """
        return self._data["screens"][u]

    def get_view_by_uuid(self, u: UUID) -> dict:
        """Get a view by its UUID, giving an error if it can't be found
        """
        return self._data["views"][u]

    def get_pattern_by_uuid(self, u: UUID) -> dict:
        """Get a pattern by its UUID, giving an error if it can't be found
        """
        return self._data["patterns"][u]

    def _get_by_name(self, store: str, name: str) -> dict:
        """Get a set of data by name, using store to select 
        "screens" "views" or "patterns"
        """
        for d in self._data[store].values():
            if "name" in d and d["name"] == name:
                return d
        raise KeyError(name)

    def get_pattern_by_name(self, u: str) -> dict:
        """Get the first pattern with the matching name, giving an error if it can't be found
        """
        return self._get_by_name("patterns", u)

    def get_screen_by_name(self, u: str) -> dict:
        """Get the first screen with the matching name, giving an error if it can't be found
        """
        return self._get_by_name("screens", u)

    def get_view_by_name(self, u: str) -> dict:
        """Get the first view with the matching name, giving an error if it can't be found
        """
        return self._get_by_name("views", u)

    def connect_pattern_to_view(
        self,
        pattern_id: UUID,
        view_id: UUID,
        coefficient=1,
        transform={
            "position": (0, 0),
            "size": (0, 0),
            "rotation": 0
        }
    ) -> bool:
        """Connect the given pattern to the given view
        coefficient should be the coefficient to multiply the view by and transform should 
        be its transform. 
        If there is already a pattern reference in the view, the coefficient and transform 
        will be overridden with the new values

        returns True if the function succeeds in making the connection, False otherwise
        """
        try:
            v = self.get_view_by_uuid(view_id)
            v["patterns"] = [coefficient, transform]
        except KeyError as e:
            return False
        return True

    def add_pattern(self, pattern: dict):
        """Add the given pattern. 
        pattern should have at least an id and a type.
        Replaces a pattern if one already had the same ID
        """
        self._data["patterns"][pattern["id"]] = pattern

    def remove_pattern(self, pattern_id: UUID) -> bool:
        """Remove the given pattern id.
        Returns True if the pattern was in the dictionary
        Returns False if it wasn't
        """
        try:
            # remove all pattern references from the views
            for v in self._data["views"].values():
                try:
                    v["patterns"].pop(pattern_id)
                except KeyError:
                    pass
            # remove from patterns
            self._data["patterns"].pop(pattern_id)
            return True
        except KeyError:
            return False

    def add_view(self, view: dict):
        """Add a view to the views    
        if the view already existed, replace the data of the view
        """
        self._data["views"][view["id"]] = view

    def remove_view(self, view_id: UUID) -> bool:
        """Remove the given view by id.
        Returns True if the view was in the dictionary.
        Returns False otherwise
        """
        try:
            # remove all view references from the screens
            for s in self._data["screens"].values():
                try:
                    s["views"].pop(view_id)
                except KeyError:
                    pass
            # remove from patterns
            self._data["views"].pop(view_id)
            return True
        except KeyError:
            return False
