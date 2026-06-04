class RAGError(Exception):
    ...


class OllamaServerError(RAGError):
    ...


class ModelNotFoundError(RAGError):
    ...


class DocumentNotFoundError(RAGError):
    ...
