#!/usr/bin/env python
# coding: utf-8

class PostProcessor:
    def __call__(self, doc_obj):
        pass

def create_postprocessor():
    #TODO factory
    return PostProcessor()
