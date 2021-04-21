from flask import Flask,jsonify,request,make_response
from http import HTTPStatus #to display error codes
from flask_sqlalchemy import SQLAlchemy  #databse used
from marshmallow import fields,ValidationError #for ValidationError
from marshmallow_sqlalchemy import ModelSchema #to give schema to database
from sqlalchemy.types import TypeDecorator #to identify the type of the data
from sqlalchemy import create_engine #to create databsse
from sqlalchemy.orm import scoped_session, sessionmaker #to manage the session of databse creation
from sqlalchemy.ext.declarative import declarative_base #base class




def page_not_found(e):  #when wrong URL passed
    return jsonify({'message': 'URL not found !!'}), HTTPStatus.NOT_FOUND
def BAD_REQUEST(e): #check syntax error
    return jsonify({'message': 'BAD REQUEST !! Syntax,Invalid Request Message Framing,Or Deceptive Request Routing'}),HTTPStatus.BAD_REQUEST
def method_not_allowed(e): # when you pass wrong url to a method
    return jsonify({'message': 'Method Not Allowed !!'}), HTTPStatus.METHOD_NOT_ALLOWED


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///tablet.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

engine = create_engine('sqlite:///tablet.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    Base.metadata.create_all(bind=engine)

app.register_error_handler(404,page_not_found) #to register the above defined error functions 
app.register_error_handler(400,BAD_REQUEST)
app.register_error_handler(405,method_not_allowed)
db=SQLAlchemy(app)


class tablet(db.Model): #tablet table definition
    tablet_id=db.Column(db.Integer,primary_key=True)
    tablet_name=db.Column(db.String(20),nullable=False)
    tablet_quantity=db.Column(db.Integer,nullable=False)
    tablet_cost=db.Column(db.Integer,nullable=False)
    

    def create(self):
       db.session.add(self)
       db.session.commit()
       return self

    def __init__(self,tablet_name,tablet_quantity,tablet_cost):
            self.tablet_name = tablet_name
            self.tablet_quantity= tablet_quantity
            self.tablet_cost=tablet_cost

    def __repr__(self):
                return f"{self.tablet_id}"




def must_not_be_blank(data): #validation to check for empty fileds passed
    if not data:
        raise ValidationError("Can't be Empty!") #raise Validation error on empty input data

def null_and_type_check(data, tabletObject): #check for data input type for all fields in table ; quantity should be between 5 and 100 ; cost should be above 5
   messageString = []
   emptyVariables = []   
   if data.get('tablet_name'):
      tabletObject.tablet_name = data['tablet_name']
      if type(tabletObject.tablet_name)!=str:
         messageString.append("Incorrect data type: Tablet name needs to be String")
      if type(tabletObject.tablet_name)==str and data.get('tablet_name').strip() == '':
         emptyVariables.append("Empty Field Error: Tablet Name cannot be empty")
   else:
      emptyVariables.append("Empty Field Error: Tablet Name cannot be empty")
   if data.get('tablet_quantity'):
      tabletObject.tablet_quantity = data['tablet_quantity']
      if type(tabletObject.tablet_quantity)!=int:
         messageString.append("Incorrect data type: Tablet quantity needs to be Integer")
      if type(tabletObject.tablet_quantity)==int and data.get('tablet_quantity') == '':
         emptyVariables.append("Empty Field Error: Tablet quantity cannot be empty")
      if tabletObject.tablet_quantity < 5 or tabletObject.tablet_quantity > 100:
        messageString.append("Invalid quantity: tablet quantity should be between 5 and 100")
   else:
      emptyVariables.append("Empty Field Error: Tablet quantity cannot be empty")
   if data.get('tablet_cost'):
      tabletObject.tablet_cost = data['tablet_cost']
      if type(tabletObject.tablet_cost)!=int:
         messageString.append("Incorrect data type: Tablet cost needs to be Integer")
      if type(tabletObject.tablet_cost)==int and data.get('tablet_cost') == '':
         emptyVariables.append("Empty Field Error: Tablet cost cannot be empty")
      if tabletObject.tablet_cost < 5 :
        messageString.append("Invalid cost: tablet cost should be greater than 5")
   else:
      emptyVariables.append("Empty Field Error: Tablet cost cannot be empty")
   output = emptyVariables + messageString
   if output:
      return ', '.join(output)
   else:
      return '' 
        

class tabletSchema(ModelSchema): #to get and post the data from table 
      class Meta(ModelSchema.Meta):
           model = tablet
           sqla_session = db.session
      tablet_id = fields.Integer(dump_only=True)
      tablet_name = fields.String(required=True,validate=must_not_be_blank) 
      tablet_quantity = fields.Integer(required=True,validate=must_not_be_blank) 
      tablet_cost = fields.Integer(required=True,validate=must_not_be_blank)


# Get All tablets    
@app.route('/tablets', methods=['GET'])
def get_all_tablets():
   
   get_all = tablet.query.all()
   tablet_schema = tabletSchema(many=True)
   tablets = tablet_schema.dump(get_all)
   if tablets:
      return make_response(jsonify({"Tablets": tablets}),HTTPStatus.OK)
   return jsonify({'message': 'tablet not found !'}), HTTPStatus.NOT_FOUND

# Get tablet By id's
@app.route('/tablets/<int:tablet_id>', methods=['GET'])
def get_tablet_by_id(tablet_id):
   get_tab = tablet.query.get(tablet_id)
   tablet_schema = tabletSchema()
   tablets = tablet_schema.dump(get_tab)
   if tablets:
          return make_response(jsonify({"Tablets": tablets}),HTTPStatus.OK)
   return jsonify({'message': 'tablet not found'}), HTTPStatus.NOT_FOUND

#Add tablet
@app.route('/tablets', methods=['POST'])
def add_tablet():
   data = request.get_json()
   if not data:
        return {"message": "No input data provided"},400 
   tablet_schema = tabletSchema()
   try:
      tablets = tablet_schema.load(data)
   except ValidationError as err:
        return err.messages, 422    
   improper_data = null_and_type_check(data, tablets)
   if improper_data:
      return {"message": improper_data}, 422
   results = tablet_schema.dump(tablets.create())
   return make_response(jsonify({"Tablet": results})),HTTPStatus.CREATED
   
#Update tablet
@app.route('/tablets/<int:tablet_id>', methods=['PUT'])
def update_tablets(tablet_id):
      data=request.get_json()
      if not data:
        return {"message": "No input data provided"} ,400 
      get_tablet=tablet.query.get(tablet_id)
      if(get_tablet == None):
         return {"message": "Tablet id doesn't exist, can't update!"}, 404
      improperData = null_and_type_check(data, get_tablet) 
      if improperData:
            return {"message": improperData}, 422
      db.session.add(get_tablet)
      db.session.commit()
      tablet_schema = tabletSchema(only=['tablet_id', 'tablet_name', 'tablet_quantity', 'tablet_cost'])
      tablets = tablet_schema.dump(get_tablet)
      if tablets:
          return make_response(jsonify({"Tablet": tablets})),HTTPStatus.OK
      return jsonify({'message': 'tablet with tabletid not found'}),HTTPStatus.NOT_FOUND 
     
#Delete tablet By ID
@app.route('/tablets/<int:tablet_id>', methods=['DELETE'])
def delete_tablet_by_id(tablet_id):
   get_tablet = tablet.query.get(tablet_id)
   if get_tablet:
      db.session.delete(get_tablet)
      db.session.commit()
      return make_response(jsonify({'message':'Tablet Deleted!'})),HTTPStatus.OK 
   return jsonify({'message': 'tablet not found'}), HTTPStatus.NOT_FOUND  



  

if __name__=="__main__":
    app.run(debug=True,host='0.0.0.0',port='5000')
