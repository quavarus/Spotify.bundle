
def addAttribute(obj, attributeName, attributeValue):
  enableAttribute(obj,attributeName)
  obj._attributes[attributeName]=attributeValue
  return obj
  
def enableAttribute(obj, attributeName):
  obj._attribute_list.append(attributeName)
  return obj

def getAttribute(obj, attributeName):
  return obj._attributes[attributeName]

def removeAttribute(obj, attributeName):
  del obj._attributes[attributeName]

def getRequest(request):
   return request._context.request

def getContext(request):
   return request._context

def getSandbox(request):
	return request._context._sandbox

def evaluate(expression, globals=None, locals=None):
  return eval(expression, globals, locals)